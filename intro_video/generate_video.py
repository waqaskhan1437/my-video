#!/usr/bin/env python3
"""
Video Workflow Manager - Professional Introduction Video Generator
Generates slides + voiceover + subtitles + final video automatically
"""

import asyncio
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont

try:
    import edge_tts
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

# ============================================================
# CONFIGURATION
# ============================================================
WIDTH = 1920
HEIGHT = 1080
FPS = 30
VOICE = "en-US-AndrewNeural"  # Professional warm male
OUTPUT_DIR = Path(__file__).parent / "output"
FRAMES_DIR = OUTPUT_DIR / "frames"
AUDIO_DIR = OUTPUT_DIR / "audio"
OUTPUT_DIR.mkdir(exist_ok=True)
FRAMES_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# Colors
BG_DARK = (13, 13, 20)
BG_CARD = (26, 26, 36)
ACCENT_BLUE = (99, 102, 241)    # Indigo
ACCENT_CYAN = (34, 211, 238)
ACCENT_GREEN = (34, 197, 94)
ACCENT_ORANGE = (249, 115, 22)
ACCENT_PINK = (236, 72, 153)
ACCENT_PURPLE = (168, 85, 247)
WHITE = (255, 255, 255)
GRAY = (156, 163, 175)
LIGHT_GRAY = (209, 213, 219)
DARK_GRAY = (75, 85, 99)

# Font paths
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BLACK = "C:/Windows/Fonts/ariblk.ttf"

# ============================================================
# VIDEO SCRIPT - Each section with text for voiceover
# ============================================================
SECTIONS = [
    {
        "id": "hook",
        "duration": 7,
        "voice_text": "What if your entire video workflow, from fetching raw footage to posting branded shorts on every social platform, ran completely on autopilot?",
        "slide_type": "title_hook",
        "title": "VIDEO WORKFLOW",
        "subtitle": "MANAGER",
        "tagline": "Fully Automated Video Pipeline",
    },
    {
        "id": "problem",
        "duration": 10,
        "voice_text": "Every day, content creators and agencies waste hours downloading videos, editing them into shorts, adding captions, writing taglines, and manually posting to YouTube, TikTok, Instagram, and Facebook. It's repetitive, exhausting, and it doesn't scale.",
        "slide_type": "problem",
        "title": "The Problem",
        "bullets": [
            "Hours wasted on repetitive editing tasks",
            "Manual posting to 9+ social platforms",
            "No captions, no branding, no consistency",
            "Impossible to scale content production",
        ],
    },
    {
        "id": "solution",
        "duration": 8,
        "voice_text": "Introducing Video Workflow Manager. A powerful automation engine that fetches your videos, converts them into branded shorts with AI captions and taglines, and posts them everywhere, automatically.",
        "slide_type": "solution_intro",
        "title": "The Solution",
        "subtitle": "Video Workflow Manager",
        "tagline": "Fetch. Process. Post. Automatically.",
    },
    {
        "id": "feature_fetch",
        "duration": 8,
        "voice_text": "Connect any video source. Bunny CDN, FTP servers, or any cloud storage. The system fetches your videos automatically with smart date filtering and rotation to ensure every video gets processed.",
        "slide_type": "feature",
        "icon_text": "1",
        "title": "Smart Video Fetching",
        "bullets": [
            "Bunny CDN Stream API integration",
            "FTP / HTTP storage support",
            "Date range & rotation filtering",
            "Auto-skip already processed videos",
        ],
        "accent": ACCENT_BLUE,
    },
    {
        "id": "feature_process",
        "duration": 9,
        "voice_text": "FFmpeg powers the video engine. Convert any video into six different aspect ratios: vertical for Shorts and Reels, square for feeds, or widescreen. Choose crop or fit mode. Set custom durations and let the smart segment selector find the best starting point.",
        "slide_type": "feature",
        "icon_text": "2",
        "title": "FFmpeg Video Processing",
        "bullets": [
            "6 aspect ratios: 9:16, 1:1, 16:9 + fit modes",
            "Smart segment selection",
            "Custom duration control",
            "High quality H.264 encoding",
        ],
        "accent": ACCENT_CYAN,
    },
    {
        "id": "feature_captions",
        "duration": 8,
        "voice_text": "Auto-generate captions in over twenty languages with OpenAI Whisper. Word-level timestamps ensure perfectly synced subtitles that are burned directly into your videos for maximum engagement.",
        "slide_type": "feature",
        "icon_text": "3",
        "title": "AI-Powered Captions",
        "bullets": [
            "OpenAI Whisper transcription",
            "20+ languages supported",
            "Word-level timestamps",
            "Styled subtitles burned into video",
        ],
        "accent": ACCENT_GREEN,
    },
    {
        "id": "feature_taglines",
        "duration": 9,
        "voice_text": "Never run out of creative taglines. The AI engine uses Google Gemini or OpenAI to generate unique, engaging text for every single video. Plus, a built-in library of over five thousand viral taglines with emojis as an instant fallback.",
        "slide_type": "feature",
        "icon_text": "4",
        "title": "AI Tagline Generator",
        "bullets": [
            "Google Gemini (FREE) or OpenAI",
            "Unique taglines per video",
            "5,000+ built-in viral taglines",
            "Emoji overlays with Twemoji PNGs",
        ],
        "accent": ACCENT_ORANGE,
    },
    {
        "id": "feature_posting",
        "duration": 9,
        "voice_text": "Post to nine platforms simultaneously. YouTube Shorts, TikTok, Instagram Reels, Facebook, Threads, X, LinkedIn, Pinterest, and Bluesky. Schedule posts with custom timing, stagger them for maximum reach, or publish immediately.",
        "slide_type": "feature",
        "icon_text": "5",
        "title": "9-Platform Publishing",
        "bullets": [
            "YouTube, TikTok, Instagram, Facebook",
            "Threads, X, LinkedIn, Pinterest, Bluesky",
            "Scheduled & staggered posting",
            "AI-generated titles, descriptions, hashtags",
        ],
        "accent": ACCENT_PINK,
    },
    {
        "id": "feature_schedule",
        "duration": 8,
        "voice_text": "Set it and forget it. Schedule automations to run every few minutes, hourly, daily, or weekly. The built-in cron system handles everything with live progress tracking, detailed logs, and automatic error recovery.",
        "slide_type": "feature",
        "icon_text": "6",
        "title": "Automated Scheduling",
        "bullets": [
            "Minute, hourly, daily, weekly schedules",
            "Live progress tracking & SSE streaming",
            "Detailed activity logs",
            "Auto-recovery from errors",
        ],
        "accent": ACCENT_PURPLE,
    },
    {
        "id": "architecture",
        "duration": 8,
        "voice_text": "Built with battle-tested technology. PHP backend running on XAMPP, MySQL database with auto-migration, FFmpeg for video processing, and a modern dark-themed dashboard powered by Tailwind CSS. Everything self-hosted, fully under your control.",
        "slide_type": "tech_stack",
        "title": "Built With Proven Technology",
        "techs": [
            ("PHP 8.0+", "Backend Engine"),
            ("MySQL", "Database"),
            ("FFmpeg", "Video Processing"),
            ("Tailwind CSS", "Modern UI"),
            ("OpenAI Whisper", "Captions"),
            ("Gemini AI", "Taglines"),
        ],
    },
    {
        "id": "stats",
        "duration": 7,
        "voice_text": "The numbers speak for themselves. Nineteen thousand lines of production code, two hundred forty three functions, twenty three API endpoints, nine social platforms, six aspect ratios, and five thousand plus taglines ready to go.",
        "slide_type": "stats",
        "title": "By The Numbers",
        "stats": [
            ("19,195", "Lines of Code"),
            ("243", "Functions"),
            ("23", "API Endpoints"),
            ("9", "Social Platforms"),
            ("6", "Aspect Ratios"),
            ("5,000+", "Built-in Taglines"),
        ],
    },
    {
        "id": "workflow",
        "duration": 8,
        "voice_text": "Here's the complete workflow in action. Configure once: set your video source, choose your style, enable AI features, select platforms. Then hit start. The engine fetches, processes, brands, captions, and posts, all automatically, every single time.",
        "slide_type": "workflow",
        "title": "Complete Workflow",
        "steps": [
            "Configure Video Source",
            "Set Aspect Ratio & Style",
            "Enable AI Captions & Taglines",
            "Select Social Platforms",
            "Hit Start - Runs Automatically!",
        ],
    },
    {
        "id": "cta",
        "duration": 8,
        "voice_text": "Ready to automate your entire video pipeline? Video Workflow Manager is your all-in-one solution for content automation at scale. Self-hosted, fully customizable, and built to save you hours every single day. Let's get started.",
        "slide_type": "cta",
        "title": "Ready to Automate?",
        "subtitle": "Video Workflow Manager",
        "tagline": "Your All-in-One Video Automation Engine",
    },
]


# ============================================================
# DRAWING HELPERS
# ============================================================
def get_font(bold=False, size=48, black=False):
    path = FONT_BLACK if black else (FONT_BOLD if bold else FONT_REGULAR)
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def draw_rounded_rect(draw, xy, radius, fill, outline=None):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def draw_gradient_bar(img, y, height, color_start, color_end):
    draw = ImageDraw.Draw(img)
    for x in range(WIDTH):
        ratio = x / WIDTH
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(x, y), (x, y + height)], fill=(r, g, b))


def draw_glow_circle(img, cx, cy, radius, color, alpha=80):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for r in range(radius, 0, -2):
        a = int(alpha * (r / radius))
        odraw.ellipse(
            [cx - r, cy - r, cx + r, cy + r],
            fill=(color[0], color[1], color[2], a),
        )
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))


def center_text(draw, text, y, font, fill=WHITE):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, y), text, fill=fill, font=font)


def draw_particle_bg(img, seed=42):
    """Draw subtle animated particle dots on background"""
    import random
    random.seed(seed)
    draw = ImageDraw.Draw(img)
    for _ in range(60):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        size = random.randint(1, 3)
        alpha = random.randint(20, 60)
        draw.ellipse([x, y, x + size, y + size], fill=(255, 255, 255, alpha) if img.mode == "RGBA" else (40, 40, 55))


# ============================================================
# SLIDE GENERATORS
# ============================================================
def create_base_slide(seed=0):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw_gradient_bar(img, 0, 4, ACCENT_BLUE, ACCENT_CYAN)
    draw_particle_bg(img, seed)
    return img


def slide_title_hook(section):
    img = create_base_slide(1)
    draw = ImageDraw.Draw(img)
    draw_glow_circle(img, WIDTH // 2, HEIGHT // 2, 300, ACCENT_BLUE, 30)
    draw = ImageDraw.Draw(img)

    # Main title
    font_big = get_font(black=True, size=96)
    center_text(draw, section["title"], 280, font_big, ACCENT_CYAN)

    # Subtitle
    font_sub = get_font(black=True, size=88)
    center_text(draw, section["subtitle"], 390, font_sub, WHITE)

    # Divider line
    draw.rectangle([WIDTH // 2 - 200, 510, WIDTH // 2 + 200, 514], fill=ACCENT_BLUE)

    # Tagline
    font_tag = get_font(size=36)
    center_text(draw, section["tagline"], 545, font_tag, GRAY)

    # Bottom accent
    draw_gradient_bar(img, HEIGHT - 6, 6, ACCENT_CYAN, ACCENT_BLUE)
    return img


def slide_problem(section):
    img = create_base_slide(2)
    draw = ImageDraw.Draw(img)
    draw_glow_circle(img, 200, 200, 250, (220, 38, 38), 20)
    draw = ImageDraw.Draw(img)

    font_title = get_font(black=True, size=64)
    center_text(draw, section["title"], 120, font_title, (239, 68, 68))

    font_bullet = get_font(size=36)
    y = 280
    for i, bullet in enumerate(section["bullets"]):
        # Red bullet icon
        bx = 300
        draw.rounded_rectangle([bx, y + 5, bx + 30, y + 35], radius=5, fill=(220, 38, 38))
        draw.text((bx + 8, y + 4), "X", fill=WHITE, font=get_font(bold=True, size=24))
        draw.text((bx + 50, y), bullet, fill=LIGHT_GRAY, font=font_bullet)
        y += 80

    # Warning box
    draw.rounded_rectangle([300, y + 40, WIDTH - 300, y + 130], radius=15, fill=(60, 20, 20))
    draw.rounded_rectangle([300, y + 40, WIDTH - 300, y + 130], radius=15, outline=(220, 38, 38))
    warn_font = get_font(bold=True, size=28)
    center_text(draw, "This workflow does NOT scale manually.", y + 60, warn_font, (239, 68, 68))

    return img


def slide_solution_intro(section):
    img = create_base_slide(3)
    draw = ImageDraw.Draw(img)
    draw_glow_circle(img, WIDTH // 2, HEIGHT // 2, 350, ACCENT_GREEN, 25)
    draw = ImageDraw.Draw(img)

    font_label = get_font(size=32)
    center_text(draw, section["title"], 200, font_label, ACCENT_GREEN)

    font_name = get_font(black=True, size=80)
    center_text(draw, section["subtitle"], 270, font_name, WHITE)

    draw.rectangle([WIDTH // 2 - 180, 380, WIDTH // 2 + 180, 384], fill=ACCENT_GREEN)

    font_tag = get_font(bold=True, size=40)
    center_text(draw, section["tagline"], 420, font_tag, ACCENT_CYAN)

    # Feature preview boxes
    features = ["Fetch", "Process", "Brand", "Caption", "Post"]
    box_w = 180
    total_w = len(features) * box_w + (len(features) - 1) * 20
    start_x = (WIDTH - total_w) // 2
    for i, feat in enumerate(features):
        x = start_x + i * (box_w + 20)
        colors = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_ORANGE, ACCENT_GREEN, ACCENT_PINK]
        draw.rounded_rectangle([x, 550, x + box_w, 620], radius=12, fill=colors[i % len(colors)])
        f = get_font(bold=True, size=24)
        bbox = draw.textbbox((0, 0), feat, font=f)
        tw = bbox[2] - bbox[0]
        draw.text((x + (box_w - tw) // 2, 568), feat, fill=WHITE, font=f)

        if i < len(features) - 1:
            arrow_x = x + box_w + 2
            draw.text((arrow_x, 568), "->", fill=GRAY, font=get_font(size=22))

    return img


def slide_feature(section):
    img = create_base_slide(hash(section["id"]) % 100)
    draw = ImageDraw.Draw(img)
    accent = section.get("accent", ACCENT_BLUE)
    draw_glow_circle(img, 250, 350, 200, accent, 20)
    draw = ImageDraw.Draw(img)

    # Number circle
    draw.ellipse([120, 150, 220, 250], fill=accent)
    num_font = get_font(black=True, size=56)
    bbox = draw.textbbox((0, 0), section["icon_text"], font=num_font)
    nw = bbox[2] - bbox[0]
    draw.text((170 - nw // 2, 170), section["icon_text"], fill=WHITE, font=num_font)

    # Title
    font_title = get_font(black=True, size=56)
    draw.text((260, 170), section["title"], fill=WHITE, font=font_title)

    # Divider
    draw.rectangle([120, 280, 600, 284], fill=accent)

    # Bullets with checkmarks
    font_bullet = get_font(size=34)
    y = 330
    for bullet in section["bullets"]:
        draw.rounded_rectangle([140, y + 2, 174, y + 36], radius=6, fill=accent)
        draw.text((145, y), ">>", fill=WHITE, font=get_font(bold=True, size=20))
        draw.text((195, y), bullet, fill=LIGHT_GRAY, font=font_bullet)
        y += 75

    # Right side decorative element
    draw.rounded_rectangle([WIDTH - 450, 150, WIDTH - 100, HEIGHT - 150], radius=20, fill=BG_CARD, outline=(50, 50, 70))
    # Fake UI elements inside
    for i in range(5):
        bar_y = 200 + i * 70
        bar_w = 250 - i * 30
        draw.rounded_rectangle(
            [WIDTH - 400, bar_y, WIDTH - 400 + bar_w, bar_y + 20],
            radius=5, fill=(*accent, 100) if img.mode == "RGBA" else tuple(c // 2 for c in accent)
        )
        draw.rounded_rectangle(
            [WIDTH - 400, bar_y + 30, WIDTH - 200, bar_y + 40],
            radius=3, fill=DARK_GRAY
        )

    return img


def slide_tech_stack(section):
    img = create_base_slide(10)
    draw = ImageDraw.Draw(img)

    font_title = get_font(black=True, size=56)
    center_text(draw, section["title"], 100, font_title, WHITE)
    draw.rectangle([WIDTH // 2 - 150, 175, WIDTH // 2 + 150, 179], fill=ACCENT_BLUE)

    techs = section["techs"]
    cols = 3
    rows = 2
    box_w = 380
    box_h = 160
    gap = 40
    total_w = cols * box_w + (cols - 1) * gap
    total_h = rows * box_h + (rows - 1) * gap
    start_x = (WIDTH - total_w) // 2
    start_y = 240

    colors = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_CYAN, ACCENT_ORANGE, ACCENT_PINK, ACCENT_PURPLE]

    for i, (name, desc) in enumerate(techs):
        r = i // cols
        c = i % cols
        x = start_x + c * (box_w + gap)
        y = start_y + r * (box_h + gap)

        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=15, fill=BG_CARD, outline=colors[i])

        # Color accent bar at top of card
        draw.rounded_rectangle([x, y, x + box_w, y + 6], radius=3, fill=colors[i])

        f_name = get_font(bold=True, size=36)
        draw.text((x + 30, y + 35), name, fill=WHITE, font=f_name)

        f_desc = get_font(size=24)
        draw.text((x + 30, y + 90), desc, fill=GRAY, font=f_desc)

    return img


def slide_stats(section):
    img = create_base_slide(11)
    draw = ImageDraw.Draw(img)

    font_title = get_font(black=True, size=56)
    center_text(draw, section["title"], 80, font_title, WHITE)

    stats = section["stats"]
    cols = 3
    rows = 2
    box_w = 350
    box_h = 180
    gap = 50
    total_w = cols * box_w + (cols - 1) * gap
    start_x = (WIDTH - total_w) // 2
    start_y = 220

    colors = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PINK, ACCENT_PURPLE]

    for i, (number, label) in enumerate(stats):
        r = i // cols
        c = i % cols
        x = start_x + c * (box_w + gap)
        y = start_y + r * (box_h + gap)

        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=15, fill=BG_CARD)
        # Accent left bar
        draw.rounded_rectangle([x, y + 20, x + 5, y + box_h - 20], radius=3, fill=colors[i])

        f_num = get_font(black=True, size=60)
        bbox = draw.textbbox((0, 0), number, font=f_num)
        nw = bbox[2] - bbox[0]
        draw.text((x + (box_w - nw) // 2, y + 30), number, fill=colors[i], font=f_num)

        f_label = get_font(size=24)
        bbox = draw.textbbox((0, 0), label, font=f_label)
        lw = bbox[2] - bbox[0]
        draw.text((x + (box_w - lw) // 2, y + 115), label, fill=GRAY, font=f_label)

    return img


def slide_workflow(section):
    img = create_base_slide(12)
    draw = ImageDraw.Draw(img)

    font_title = get_font(black=True, size=56)
    center_text(draw, section["title"], 80, font_title, WHITE)

    steps = section["steps"]
    box_h = 80
    box_w = 700
    gap = 30
    total_h = len(steps) * box_h + (len(steps) - 1) * gap
    start_y = (HEIGHT - total_h) // 2 + 30
    start_x = (WIDTH - box_w) // 2

    colors = [ACCENT_BLUE, ACCENT_CYAN, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PINK]

    for i, step in enumerate(steps):
        y = start_y + i * (box_h + gap)
        color = colors[i % len(colors)]

        draw.rounded_rectangle([start_x, y, start_x + box_w, y + box_h], radius=15, fill=BG_CARD, outline=color)

        # Step number
        draw.ellipse([start_x + 15, y + 15, start_x + 65, y + 65], fill=color)
        n_font = get_font(bold=True, size=28)
        num = str(i + 1)
        bbox = draw.textbbox((0, 0), num, font=n_font)
        nw = bbox[2] - bbox[0]
        draw.text((start_x + 40 - nw // 2, y + 23), num, fill=WHITE, font=n_font)

        # Step text
        f_step = get_font(bold=True, size=32)
        draw.text((start_x + 85, y + 22), step, fill=WHITE, font=f_step)

        # Arrow connector
        if i < len(steps) - 1:
            ax = start_x + box_w // 2
            ay = y + box_h
            draw.polygon([(ax - 8, ay + 5), (ax + 8, ay + 5), (ax, ay + gap - 5)], fill=color)

    return img


def slide_cta(section):
    img = create_base_slide(99)
    draw = ImageDraw.Draw(img)
    draw_glow_circle(img, WIDTH // 2, HEIGHT // 2, 400, ACCENT_BLUE, 30)
    draw_glow_circle(img, WIDTH // 2, HEIGHT // 2, 250, ACCENT_CYAN, 20)
    draw = ImageDraw.Draw(img)

    font_ask = get_font(bold=True, size=44)
    center_text(draw, section["title"], 220, font_ask, ACCENT_CYAN)

    font_name = get_font(black=True, size=80)
    center_text(draw, section["subtitle"], 300, font_name, WHITE)

    draw.rectangle([WIDTH // 2 - 200, 410, WIDTH // 2 + 200, 414], fill=ACCENT_BLUE)

    font_tag = get_font(size=36)
    center_text(draw, section["tagline"], 450, font_tag, LIGHT_GRAY)

    # CTA Button
    btn_w = 500
    btn_h = 70
    btn_x = (WIDTH - btn_w) // 2
    btn_y = 560
    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h], radius=35, fill=ACCENT_BLUE)
    f_btn = get_font(bold=True, size=32)
    center_text(draw, "Get Started Today", btn_y + 16, f_btn, WHITE)

    # Bottom gradient bar
    draw_gradient_bar(img, HEIGHT - 6, 6, ACCENT_BLUE, ACCENT_CYAN)

    return img


SLIDE_GENERATORS = {
    "title_hook": slide_title_hook,
    "problem": slide_problem,
    "solution_intro": slide_solution_intro,
    "feature": slide_feature,
    "tech_stack": slide_tech_stack,
    "stats": slide_stats,
    "workflow": slide_workflow,
    "cta": slide_cta,
}


# ============================================================
# MAIN PIPELINE
# ============================================================
def step1_generate_slides():
    print("\n=== STEP 1: Generating Slides ===")
    for i, section in enumerate(SECTIONS):
        generator = SLIDE_GENERATORS[section["slide_type"]]
        img = generator(section)
        path = FRAMES_DIR / f"{i:02d}_{section['id']}.png"
        img.save(str(path), quality=95)
        print(f"  [{i+1}/{len(SECTIONS)}] Created: {path.name}")
    print(f"  DONE: {len(SECTIONS)} slides generated")


async def step2_generate_voiceover():
    print("\n=== STEP 2: Generating Voiceover ===")
    for i, section in enumerate(SECTIONS):
        audio_path = AUDIO_DIR / f"{i:02d}_{section['id']}.mp3"
        srt_path = AUDIO_DIR / f"{i:02d}_{section['id']}.srt"

        # Generate audio + subtitles in one pass
        communicate = edge_tts.Communicate(
            section["voice_text"],
            VOICE,
            rate="+8%",
            pitch="-2Hz",
        )
        sub_maker = edge_tts.SubMaker()

        with open(str(audio_path), "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                else:
                    sub_maker.feed(chunk)

        with open(str(srt_path), "w", encoding="utf-8") as f:
            f.write(sub_maker.get_srt())

        print(f"  [{i+1}/{len(SECTIONS)}] Audio: {audio_path.name}")
    print(f"  DONE: {len(SECTIONS)} voiceover clips generated")


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def step3_create_section_videos():
    print("\n=== STEP 3: Creating Section Videos ===")
    for i, section in enumerate(SECTIONS):
        slide_path = FRAMES_DIR / f"{i:02d}_{section['id']}.png"
        audio_path = AUDIO_DIR / f"{i:02d}_{section['id']}.mp3"
        video_path = OUTPUT_DIR / f"{i:02d}_{section['id']}.mp4"

        duration = get_audio_duration(audio_path)
        duration += 0.8  # small padding

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(slide_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-vf", f"scale={WIDTH}:{HEIGHT}",
            "-t", f"{duration:.2f}",
            "-shortest",
            str(video_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"  [{i+1}/{len(SECTIONS)}] Video: {video_path.name} ({duration:.1f}s)")
    print(f"  DONE: {len(SECTIONS)} section videos created")


def step4_concatenate_videos():
    print("\n=== STEP 4: Concatenating with Transitions ===")

    # Get all section video paths and durations
    videos = []
    for i, section in enumerate(SECTIONS):
        video_path = OUTPUT_DIR / f"{i:02d}_{section['id']}.mp4"
        dur = get_audio_duration(video_path)
        videos.append((video_path, dur))

    # Build concat list file (simpler approach - no complex xfade)
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(str(concat_file), "w") as f:
        for vpath, _ in videos:
            f.write(f"file '{vpath}'\n")

    concat_output = OUTPUT_DIR / "concat_raw.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        str(concat_output),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    total_dur = sum(d for _, d in videos)
    print(f"  Concatenated {len(videos)} clips -> {concat_output.name} ({total_dur:.1f}s total)")


def step5_add_subtitles_and_finalize():
    print("\n=== STEP 5: Adding Subtitles & Final Output ===")

    concat_video = OUTPUT_DIR / "concat_raw.mp4"

    # Merge all SRT files into one with correct timing offsets
    merged_srt_path = OUTPUT_DIR / "subtitles.srt"
    srt_index = 1
    offset = 0.0

    with open(str(merged_srt_path), "w", encoding="utf-8") as srt_out:
        for i, section in enumerate(SECTIONS):
            audio_path = AUDIO_DIR / f"{i:02d}_{section['id']}.mp3"
            section_srt = AUDIO_DIR / f"{i:02d}_{section['id']}.srt"
            audio_dur = get_audio_duration(audio_path) + 0.8

            if section_srt.exists():
                with open(str(section_srt), "r", encoding="utf-8") as f:
                    content = f.read()

                lines = content.strip().split("\n")
                j = 0
                while j < len(lines):
                    line = lines[j].strip()
                    if "-->" in line:
                        parts = line.split(" --> ")
                        start = parse_vtt_time(parts[0]) + offset
                        end = parse_vtt_time(parts[1]) + offset

                        j += 1
                        text = ""
                        while j < len(lines) and lines[j].strip():
                            text += lines[j].strip() + " "
                            j += 1

                        text = text.strip()
                        if text:
                            srt_out.write(f"{srt_index}\n")
                            srt_out.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
                            srt_out.write(f"{text}\n\n")
                            srt_index += 1
                    j += 1

            offset += audio_dur

    # Burn subtitles
    final_output = OUTPUT_DIR / "Video_Workflow_Manager_Introduction.mp4"

    srt_escaped = str(merged_srt_path).replace("\\", "/").replace(":", "\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(concat_video),
        "-vf", f"subtitles='{srt_escaped}':force_style='FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=1,Shadow=0,MarginV=50,Bold=1'",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(final_output),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    print(f"  FINAL VIDEO: {final_output}")
    print(f"  File size: {final_output.stat().st_size / (1024*1024):.1f} MB")


def parse_vtt_time(time_str):
    """Parse VTT/SRT time format to seconds. Handles both comma and dot milliseconds."""
    time_str = time_str.strip().replace(",", ".")
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(time_str)


def format_srt_time(seconds):
    """Format seconds to SRT time format HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{int(s):02d},{ms:03d}"


# ============================================================
# MAIN
# ============================================================
def main():
    start_time = time.time()
    print("=" * 60)
    print("  VIDEO WORKFLOW MANAGER - Introduction Video Generator")
    print("=" * 60)

    step1_generate_slides()
    asyncio.run(step2_generate_voiceover())
    step3_create_section_videos()
    step4_concatenate_videos()
    step5_add_subtitles_and_finalize()

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"  COMPLETE! Total time: {elapsed:.0f} seconds")
    print(f"  Output: {OUTPUT_DIR / 'Video_Workflow_Manager_Introduction.mp4'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
