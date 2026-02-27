#!/usr/bin/env python3
"""
Video Workflow Manager - PREMIUM Introduction Video
Handwriting + Character Animation + Professional Slides + Voiceover
"""

import asyncio
import json
import math
import os
import random
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import edge_tts
import numpy as np

# ============================================================
# CONFIG
# ============================================================
W, H = 1920, 1080
FPS = 30
OUT = Path(__file__).parent / "premium_output"
FRAMES = OUT / "frames"
AUDIO = OUT / "audio"
SCENE_VIDS = OUT / "scenes"
for d in [OUT, FRAMES, AUDIO, SCENE_VIDS]:
    d.mkdir(exist_ok=True)

VOICE = "en-US-AndrewNeural"
FB = "C:/Windows/Fonts/arialbd.ttf"
FR = "C:/Windows/Fonts/arial.ttf"
FBK = "C:/Windows/Fonts/ariblk.ttf"

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG = (13, 13, 20)
CARD = (26, 26, 36)
BLUE = (99, 102, 241)
CYAN = (34, 211, 238)
GREEN = (34, 197, 94)
ORANGE = (249, 115, 22)
PINK = (236, 72, 153)
PURPLE = (168, 85, 247)
RED = (239, 68, 68)
GRAY = (156, 163, 175)
LGRAY = (209, 213, 219)


def font(size=48, bold=False, black=False):
    p = FBK if black else (FB if bold else FR)
    try:
        return ImageFont.truetype(p, size)
    except:
        return ImageFont.load_default()


# ============================================================
# SCENE DEFINITIONS
# ============================================================
SCENES = [
    {
        "id": "s01_handwrite_hook",
        "voice": "What if your entire video workflow ran completely on autopilot? No more manual editing. No more repetitive posting. Just pure automation.",
        "type": "handwriting",
        "lines": [
            "What if your entire",
            "video workflow ran on",
            "AUTOPILOT?",
        ],
        "highlight": "AUTOPILOT?",
        "highlight_color": CYAN,
    },
    {
        "id": "s02_character_problem",
        "voice": "Every day, content creators waste hours downloading videos, editing them into shorts, writing captions, and manually posting to every platform. It's exhausting and it doesn't scale.",
        "type": "character_scene",
        "character": "tired",
        "title": "The Problem",
        "items": ["Download videos manually", "Edit into shorts one by one", "Write captions & taglines", "Post to each platform separately"],
    },
    {
        "id": "s03_handwrite_solution",
        "voice": "Introducing Video Workflow Manager. The all-in-one automation engine that handles everything for you.",
        "type": "handwriting",
        "lines": [
            "Introducing...",
            "Video Workflow Manager",
            "All-in-One Automation Engine",
        ],
        "highlight": "Video Workflow Manager",
        "highlight_color": GREEN,
    },
    {
        "id": "s04_character_fetch",
        "voice": "Step one: Connect your video source. Bunny CDN, FTP servers, or any cloud storage. The system fetches videos automatically with smart filtering and rotation.",
        "type": "character_scene",
        "character": "happy",
        "title": "Step 1: Smart Fetching",
        "items": ["Bunny CDN Stream API", "FTP & HTTP Storage", "Date range filtering", "Smart rotation system"],
    },
    {
        "id": "s05_whiteboard_process",
        "voice": "Step two: FFmpeg converts every video into six aspect ratios. Vertical for shorts, square for feeds, widescreen for YouTube. Crop or fit mode, custom durations, high quality encoding.",
        "type": "whiteboard_diagram",
        "title": "Step 2: Video Processing",
        "center": "FFmpeg\nEngine",
        "branches": ["9:16 Vertical", "1:1 Square", "16:9 Wide", "Crop Mode", "Fit Mode", "Smart Segment"],
    },
    {
        "id": "s06_handwrite_captions",
        "voice": "Step three: AI-powered captions. OpenAI Whisper transcribes in over twenty languages with word-level timestamps. Subtitles are burned directly into your videos.",
        "type": "handwriting",
        "lines": [
            "AI-Powered Captions",
            "OpenAI Whisper",
            "20+ Languages",
            "Word-Level Timestamps",
        ],
        "highlight": "OpenAI Whisper",
        "highlight_color": GREEN,
    },
    {
        "id": "s07_character_taglines",
        "voice": "Step four: Never run out of taglines. Google Gemini or OpenAI generates unique text for every video. Plus five thousand built-in viral taglines with emoji overlays.",
        "type": "character_scene",
        "character": "excited",
        "title": "Step 4: AI Taglines",
        "items": ["Google Gemini (FREE)", "OpenAI GPT integration", "5,000+ viral taglines", "Emoji PNG overlays"],
    },
    {
        "id": "s08_whiteboard_platforms",
        "voice": "Step five: Post to nine platforms simultaneously. YouTube Shorts, TikTok, Instagram Reels, Facebook, Threads, X, LinkedIn, Pinterest, and Bluesky. Scheduled or immediate.",
        "type": "whiteboard_diagram",
        "title": "Step 5: 9-Platform Publishing",
        "center": "PostForMe\nAPI",
        "branches": ["YouTube", "TikTok", "Instagram", "Facebook", "Threads", "X / Twitter"],
    },
    {
        "id": "s09_handwrite_schedule",
        "voice": "Step six: Set it and forget it. Automations run every few minutes, hourly, daily, or weekly. Live progress tracking, detailed logs, and automatic error recovery.",
        "type": "handwriting",
        "lines": [
            "Set It & Forget It",
            "Minutes | Hourly | Daily | Weekly",
            "Live Progress Tracking",
            "Auto Error Recovery",
        ],
        "highlight": "Set It & Forget It",
        "highlight_color": ORANGE,
    },
    {
        "id": "s10_stats_reveal",
        "voice": "The numbers speak for themselves. Nineteen thousand lines of code, two hundred forty three functions, twenty three API endpoints, nine social platforms, and five thousand plus taglines.",
        "type": "stats_counter",
        "stats": [
            ("19,195", "Lines of Code", BLUE),
            ("243", "Functions", CYAN),
            ("23", "API Endpoints", GREEN),
            ("9", "Platforms", ORANGE),
            ("5,000+", "Taglines", PINK),
            ("6", "Aspect Ratios", PURPLE),
        ],
    },
    {
        "id": "s11_character_workflow",
        "voice": "Here's the magic. Configure once, set your video source, choose your style, enable AI features, select platforms, hit start. The engine runs automatically, every single time.",
        "type": "character_scene",
        "character": "presenting",
        "title": "Complete Workflow",
        "items": ["Configure Video Source", "Set Style & Aspect Ratio", "Enable AI Features", "Select Platforms & Schedule", "Hit Start - Done!"],
    },
    {
        "id": "s12_handwrite_cta",
        "voice": "Ready to automate your entire video pipeline? Video Workflow Manager. Self-hosted, fully customizable, built to save you hours every single day. Let's get started.",
        "type": "handwriting",
        "lines": [
            "Ready to Automate?",
            "",
            "Video Workflow Manager",
            "Let's Get Started!",
        ],
        "highlight": "Let's Get Started!",
        "highlight_color": CYAN,
    },
]


# ============================================================
# FRAME GENERATORS
# ============================================================

def draw_stick_figure(draw, cx, cy, scale=1.0, mood="happy", color=WHITE):
    """Draw a simple stick figure character"""
    s = scale
    head_r = int(30 * s)
    # Head
    draw.ellipse([cx - head_r, cy - 100*s - head_r, cx + head_r, cy - 100*s + head_r], outline=color, width=3)
    # Body
    draw.line([(cx, cy - 100*s + head_r), (cx, cy + 20*s)], fill=color, width=3)
    # Legs
    draw.line([(cx, cy + 20*s), (cx - 30*s, cy + 80*s)], fill=color, width=3)
    draw.line([(cx, cy + 20*s), (cx + 30*s, cy + 80*s)], fill=color, width=3)

    # Arms based on mood
    if mood == "tired":
        draw.line([(cx, cy - 50*s), (cx - 40*s, cy + 10*s)], fill=color, width=3)
        draw.line([(cx, cy - 50*s), (cx + 40*s, cy + 10*s)], fill=color, width=3)
        # Sad face
        draw.arc([cx - 10*s, cy - 100*s, cx + 10*s, cy - 85*s], 0, 180, fill=RED, width=2)
        draw.ellipse([cx - 12*s, cy - 110*s, cx - 6*s, cy - 104*s], fill=color)
        draw.ellipse([cx + 6*s, cy - 110*s, cx + 12*s, cy - 104*s], fill=color)
    elif mood == "happy":
        draw.line([(cx, cy - 50*s), (cx - 50*s, cy - 80*s)], fill=color, width=3)
        draw.line([(cx, cy - 50*s), (cx + 50*s, cy - 80*s)], fill=color, width=3)
        # Happy face
        draw.arc([cx - 10*s, cy - 105*s, cx + 10*s, cy - 90*s], 180, 360, fill=GREEN, width=2)
        draw.ellipse([cx - 12*s, cy - 115*s, cx - 6*s, cy - 109*s], fill=color)
        draw.ellipse([cx + 6*s, cy - 115*s, cx + 12*s, cy - 109*s], fill=color)
    elif mood == "excited":
        draw.line([(cx, cy - 50*s), (cx - 55*s, cy - 100*s)], fill=color, width=3)
        draw.line([(cx, cy - 50*s), (cx + 55*s, cy - 100*s)], fill=color, width=3)
        # Excited face
        draw.arc([cx - 12*s, cy - 105*s, cx + 12*s, cy - 88*s], 180, 360, fill=CYAN, width=2)
        draw.text((cx - 12*s, cy - 120*s), "*", fill=CYAN, font=font(20))
        draw.text((cx + 6*s, cy - 120*s), "*", fill=CYAN, font=font(20))
    elif mood == "presenting":
        draw.line([(cx, cy - 50*s), (cx - 50*s, cy - 70*s)], fill=color, width=3)
        draw.line([(cx, cy - 50*s), (cx + 60*s, cy - 90*s)], fill=color, width=3)
        # Pointing hand indicator
        draw.polygon([(cx + 60*s, cy - 95*s), (cx + 75*s, cy - 90*s), (cx + 60*s, cy - 85*s)], fill=CYAN)
        draw.arc([cx - 10*s, cy - 105*s, cx + 10*s, cy - 92*s], 180, 360, fill=color, width=2)
        draw.ellipse([cx - 12*s, cy - 115*s, cx - 6*s, cy - 109*s], fill=color)
        draw.ellipse([cx + 6*s, cy - 115*s, cx + 12*s, cy - 109*s], fill=color)


def gen_handwriting_frames(scene, num_frames):
    """Generate handwriting animation frames"""
    frames = []
    lines = scene["lines"]
    highlight = scene.get("highlight", "")
    hl_color = scene.get("highlight_color", CYAN)

    # Calculate total characters
    all_text = "".join(lines)
    total_chars = len(all_text)
    # Use 70% of frames for writing, 30% for holding
    write_frames = int(num_frames * 0.7)
    chars_per_frame = max(1, total_chars / write_frames)

    for fi in range(num_frames):
        img = Image.new("RGB", (W, H), (250, 248, 245))  # Warm white/paper
        draw = ImageDraw.Draw(img)

        # Paper texture: faint lines
        for ly in range(100, H, 60):
            draw.line([(100, ly), (W - 100, ly)], fill=(220, 218, 215), width=1)
        # Left margin
        draw.line([(150, 50), (150, H - 50)], fill=(200, 180, 180), width=2)

        # "Pen" cursor position
        chars_shown = int(fi * chars_per_frame)
        if chars_shown > total_chars:
            chars_shown = total_chars

        char_count = 0
        y = 180
        for line in lines:
            if not line:
                y += 60
                continue

            is_highlight = (line == highlight)
            line_font = font(72, black=True) if is_highlight else font(58, bold=True)
            color = hl_color if is_highlight else (30, 30, 40)

            # Determine how much of this line to show
            line_start = char_count
            line_end = char_count + len(line)
            visible_chars = max(0, min(len(line), chars_shown - line_start))

            if visible_chars > 0:
                visible_text = line[:visible_chars]
                # Draw with slight wobble for handwriting feel
                x = 200
                for ci, ch in enumerate(visible_text):
                    wobble_y = random.randint(-2, 2)
                    draw.text((x, y + wobble_y), ch, fill=color, font=line_font)
                    bbox = draw.textbbox((0, 0), ch, font=line_font)
                    x += bbox[2] - bbox[0] + 1

                # Draw cursor/pen
                if visible_chars < len(line) and chars_shown <= total_chars:
                    # Pen tip
                    draw.ellipse([x - 3, y + 20, x + 3, y + 50], fill=(50, 50, 200))
                    draw.polygon([(x, y + 50), (x - 6, y + 35), (x + 6, y + 35)], fill=(50, 50, 200))

                if is_highlight and visible_chars == len(line):
                    # Underline for emphasis
                    bbox = draw.textbbox((200, y), visible_text, font=line_font)
                    draw.rectangle([200, bbox[3] + 5, bbox[2], bbox[3] + 9], fill=hl_color)

            char_count = line_end
            y += 100

        # Small branding corner
        draw.text((W - 350, H - 50), "Video Workflow Manager", fill=(150, 150, 155), font=font(20))

        frames.append(np.array(img))

    return frames


def gen_character_frames(scene, num_frames):
    """Generate character animation scene frames"""
    frames = []
    items = scene["items"]
    title = scene["title"]
    mood = scene.get("character", "happy")

    # Items appear one by one over 60% of duration
    items_phase = int(num_frames * 0.6)
    frames_per_item = max(1, items_phase // len(items)) if items else num_frames

    for fi in range(num_frames):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Top gradient bar
        for x in range(W):
            r = x / W
            c = (int(BLUE[0] + (CYAN[0] - BLUE[0]) * r),
                 int(BLUE[1] + (CYAN[1] - BLUE[1]) * r),
                 int(BLUE[2] + (CYAN[2] - BLUE[2]) * r))
            draw.line([(x, 0), (x, 4)], fill=c)

        # Title
        tf = font(52, black=True)
        bbox = draw.textbbox((0, 0), title, font=tf)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, 60), title, fill=WHITE, font=tf)

        # Character on the left
        char_x = 280
        char_y = 500
        # Gentle bob animation
        bob = int(5 * math.sin(fi * 0.15))
        draw_stick_figure(draw, char_x, char_y + bob, scale=2.0, mood=mood, color=LGRAY)

        # Speech bubble
        bx, by = char_x + 150, char_y - 280
        draw.rounded_rectangle([bx, by, bx + 200, by + 60], radius=15, fill=CARD, outline=CYAN)
        # Bubble pointer
        draw.polygon([(bx + 20, by + 60), (bx - 10, by + 80), (bx + 40, by + 60)], fill=CARD)

        bubble_texts = ["Let me show you!", "Watch this!", "Amazing!", "Check it out!", "Here's how!"]
        bt = bubble_texts[hash(scene["id"]) % len(bubble_texts)]
        draw.text((bx + 15, by + 15), bt, fill=CYAN, font=font(22, bold=True))

        # Items panel on right side
        panel_x = 650
        panel_y = 180
        panel_w = W - panel_x - 80
        panel_h = len(items) * 100 + 60
        draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + panel_h],
                               radius=20, fill=CARD, outline=(50, 50, 70))

        visible_items = min(len(items), fi // frames_per_item + 1) if fi < items_phase else len(items)
        colors = [BLUE, CYAN, GREEN, ORANGE, PINK]

        for idx in range(visible_items):
            iy = panel_y + 30 + idx * 100
            c = colors[idx % len(colors)]

            # Fade in effect
            item_start = idx * frames_per_item
            alpha_progress = min(1.0, (fi - item_start) / 10) if fi >= item_start else 0

            if alpha_progress > 0:
                # Checkbox
                draw.rounded_rectangle([panel_x + 25, iy + 5, panel_x + 55, iy + 35], radius=6, fill=c)
                draw.text((panel_x + 30, iy + 2), ">>", fill=WHITE, font=font(20, bold=True))

                # Text
                draw.text((panel_x + 70, iy), items[idx], fill=WHITE, font=font(32))

                # Progress line under text
                line_w = int((panel_w - 100) * alpha_progress)
                draw.rectangle([panel_x + 70, iy + 45, panel_x + 70 + line_w, iy + 47],
                               fill=(*c, 100) if len(c) == 3 else c)

        frames.append(np.array(img))
    return frames


def gen_whiteboard_frames(scene, num_frames):
    """Generate whiteboard diagram animation"""
    frames = []
    title = scene["title"]
    center_text = scene["center"]
    branches = scene["branches"]

    for fi in range(num_frames):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Top bar
        for x in range(W):
            r = x / W
            c = (int(GREEN[0] + (CYAN[0] - GREEN[0]) * r),
                 int(GREEN[1] + (CYAN[1] - GREEN[1]) * r),
                 int(GREEN[2] + (CYAN[2] - GREEN[2]) * r))
            draw.line([(x, 0), (x, 4)], fill=c)

        # Title
        tf = font(48, black=True)
        bbox = draw.textbbox((0, 0), title, font=tf)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2, 50), title, fill=WHITE, font=tf)

        cx, cy = W // 2, H // 2 + 20

        # Center node - grows in
        progress = min(1.0, fi / (num_frames * 0.15))
        cr = int(90 * progress)
        if cr > 5:
            draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=BLUE, outline=CYAN, width=3)
            if progress > 0.5:
                for li, cline in enumerate(center_text.split("\n")):
                    cf = font(24, bold=True)
                    bbox = draw.textbbox((0, 0), cline, font=cf)
                    ctw = bbox[2] - bbox[0]
                    draw.text((cx - ctw // 2, cy - 20 + li * 30), cline, fill=WHITE, font=cf)

        # Branches appear one by one
        branch_start = int(num_frames * 0.2)
        frames_per_branch = max(1, int(num_frames * 0.5) // len(branches))
        colors = [CYAN, GREEN, ORANGE, PINK, PURPLE, BLUE]
        radius = 280

        for bi, branch in enumerate(branches):
            b_start = branch_start + bi * frames_per_branch
            if fi < b_start:
                continue

            b_progress = min(1.0, (fi - b_start) / 15)
            angle = -90 + (360 / len(branches)) * bi
            rad = math.radians(angle)
            bx = cx + int(radius * math.cos(rad) * b_progress)
            by = cy + int(radius * math.sin(rad) * b_progress)
            bc = colors[bi % len(colors)]

            # Line from center
            if b_progress > 0.3:
                line_end_x = cx + int((bx - cx) * min(1.0, (b_progress - 0.3) / 0.4))
                line_end_y = cy + int((by - cy) * min(1.0, (b_progress - 0.3) / 0.4))
                draw.line([(cx, cy), (line_end_x, line_end_y)], fill=bc, width=2)

            # Branch box
            if b_progress > 0.6:
                box_alpha = min(1.0, (b_progress - 0.6) / 0.4)
                bw, bh = 140, 45
                draw.rounded_rectangle([bx - bw // 2, by - bh // 2, bx + bw // 2, by + bh // 2],
                                       radius=10, fill=CARD, outline=bc, width=2)
                bf = font(18, bold=True)
                bbox = draw.textbbox((0, 0), branch, font=bf)
                btw = bbox[2] - bbox[0]
                draw.text((bx - btw // 2, by - 12), branch, fill=WHITE, font=bf)

        frames.append(np.array(img))
    return frames


def gen_stats_frames(scene, num_frames):
    """Generate stats counter animation"""
    frames = []
    stats = scene["stats"]

    for fi in range(num_frames):
        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Top bar
        for x in range(W):
            r = x / W
            c = (int(BLUE[0] + (PINK[0] - BLUE[0]) * r),
                 int(BLUE[1] + (PINK[1] - BLUE[1]) * r),
                 int(BLUE[2] + (PINK[2] - BLUE[2]) * r))
            draw.line([(x, 0), (x, 4)], fill=c)

        # Title
        tf = font(56, black=True)
        center_text_draw(draw, "By The Numbers", 70, tf, WHITE)

        # Stats grid 3x2
        cols, rows = 3, 2
        bw, bh = 380, 190
        gap = 50
        total_w = cols * bw + (cols - 1) * gap
        sx = (W - total_w) // 2
        sy = 220

        count_progress = min(1.0, fi / (num_frames * 0.6))

        for i, (val, label, color) in enumerate(stats):
            r = i // cols
            c = i % cols
            x = sx + c * (bw + gap)
            y = sy + r * (bh + gap)

            # Card
            draw.rounded_rectangle([x, y, x + bw, y + bh], radius=15, fill=CARD)
            draw.rounded_rectangle([x, y, x + bw, y + 6], radius=3, fill=color)

            # Animated counter
            if "," in val or "+" in val:
                display_val = val if count_progress >= 0.9 else str(int(float(val.replace(",", "").replace("+", "")) * count_progress))
                if "+" in val and count_progress >= 0.9:
                    display_val = val
            else:
                try:
                    target = int(val)
                    current = int(target * count_progress)
                    display_val = str(current) if count_progress < 0.95 else val
                except:
                    display_val = val

            nf = font(56, black=True)
            bbox = draw.textbbox((0, 0), display_val, font=nf)
            nw = bbox[2] - bbox[0]
            draw.text((x + (bw - nw) // 2, y + 35), display_val, fill=color, font=nf)

            lf = font(24)
            bbox = draw.textbbox((0, 0), label, font=lf)
            lw = bbox[2] - bbox[0]
            draw.text((x + (bw - lw) // 2, y + 120), label, fill=GRAY, font=lf)

        frames.append(np.array(img))
    return frames


def center_text_draw(draw, text, y, f, fill):
    bbox = draw.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, y), text, fill=fill, font=f)


# ============================================================
# AUDIO GENERATION
# ============================================================
async def generate_all_audio():
    print("\n=== Generating Voiceover Audio ===")
    for i, scene in enumerate(SCENES):
        audio_path = AUDIO / f"{scene['id']}.mp3"
        srt_path = AUDIO / f"{scene['id']}.srt"

        communicate = edge_tts.Communicate(scene["voice"], VOICE, rate="+5%", pitch="-2Hz")
        sub_maker = edge_tts.SubMaker()

        with open(str(audio_path), "wb") as af:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    af.write(chunk["data"])
                else:
                    sub_maker.feed(chunk)

        with open(str(srt_path), "w", encoding="utf-8") as sf:
            sf.write(sub_maker.get_srt())

        print(f"  [{i+1}/{len(SCENES)}] {scene['id']}.mp3")
    print("  DONE!")


# ============================================================
# VIDEO ASSEMBLY
# ============================================================
def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True
    )
    return float(json.loads(r.stdout)["format"]["duration"])


def frames_to_video(frame_list, video_path, audio_path):
    """Write frames as PNGs then combine with ffmpeg"""
    duration = get_duration(audio_path) + 0.8
    num_needed = int(duration * FPS)

    # Extend or trim frames
    if len(frame_list) < num_needed:
        last = frame_list[-1]
        frame_list.extend([last] * (num_needed - len(frame_list)))
    elif len(frame_list) > num_needed:
        frame_list = frame_list[:num_needed]

    # Save frames as sequential PNGs
    tmp_frames = OUT / "tmp_frames"
    # Clean old frames
    if tmp_frames.exists():
        for old in tmp_frames.glob("*.png"):
            old.unlink()
    tmp_frames.mkdir(exist_ok=True)

    # Save every 3rd frame (10fps effective) with SEQUENTIAL numbering
    step = 3
    saved = []
    seq = 0
    for idx in range(0, len(frame_list), step):
        fpath = tmp_frames / f"f_{seq:06d}.png"
        Image.fromarray(frame_list[idx]).save(str(fpath))
        saved.append(fpath)
        seq += 1

    # Create video from sequential frames
    input_pattern = str(tmp_frames / "f_%06d.png")
    effective_fps = FPS // step  # 10 fps input
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(effective_fps),
        "-i", input_pattern,
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", f"fps={FPS}",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(video_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)

    # Cleanup temp frames
    for fp in saved:
        fp.unlink(missing_ok=True)


def build_scene_videos():
    print("\n=== Building Scene Videos ===")
    generators = {
        "handwriting": gen_handwriting_frames,
        "character_scene": gen_character_frames,
        "whiteboard_diagram": gen_whiteboard_frames,
        "stats_counter": gen_stats_frames,
    }

    for i, scene in enumerate(SCENES):
        audio_path = AUDIO / f"{scene['id']}.mp3"
        video_path = SCENE_VIDS / f"{scene['id']}.mp4"

        dur = get_duration(audio_path) + 0.8
        num_frames = int(dur * FPS)

        gen = generators[scene["type"]]
        random.seed(i * 42)
        frame_list = gen(scene, num_frames)

        frames_to_video(frame_list, video_path, audio_path)
        print(f"  [{i+1}/{len(SCENES)}] {scene['id']}.mp4 ({dur:.1f}s, {num_frames} frames)")

    print("  DONE!")


def concatenate_all():
    print("\n=== Concatenating Final Video ===")
    concat_file = OUT / "concat.txt"
    with open(str(concat_file), "w") as f:
        for scene in SCENES:
            vp = SCENE_VIDS / f"{scene['id']}.mp4"
            f.write(f"file '{vp}'\n")

    final_no_subs = OUT / "final_nosubs.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p",
        str(final_no_subs),
    ], capture_output=True, check=True)
    print(f"  Concatenated -> {final_no_subs.name}")


def parse_srt_time(t):
    t = t.strip().replace(",", ".")
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(t)


def fmt_srt(s):
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = s % 60
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{int(sec):02d},{ms:03d}"


def merge_subtitles_and_finalize():
    print("\n=== Adding Subtitles & Finalizing ===")
    merged = OUT / "subtitles.srt"
    idx = 1
    offset = 0.0

    with open(str(merged), "w", encoding="utf-8") as out:
        for scene in SCENES:
            audio_path = AUDIO / f"{scene['id']}.mp3"
            srt_path = AUDIO / f"{scene['id']}.srt"
            dur = get_duration(audio_path) + 0.8

            if srt_path.exists():
                content = srt_path.read_text(encoding="utf-8")
                lines = content.strip().split("\n")
                j = 0
                while j < len(lines):
                    if "-->" in lines[j]:
                        parts = lines[j].split(" --> ")
                        start = parse_srt_time(parts[0]) + offset
                        end = parse_srt_time(parts[1]) + offset
                        j += 1
                        txt = ""
                        while j < len(lines) and lines[j].strip():
                            txt += lines[j].strip() + " "
                            j += 1
                        txt = txt.strip()
                        if txt:
                            out.write(f"{idx}\n{fmt_srt(start)} --> {fmt_srt(end)}\n{txt}\n\n")
                            idx += 1
                    j += 1
            offset += dur

    # Burn subtitles
    final_no_subs = OUT / "final_nosubs.mp4"
    final = OUT / "Video_Workflow_Manager_PREMIUM.mp4"
    srt_esc = str(merged).replace("\\", "/").replace(":", "\\:")

    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(final_no_subs),
        "-vf", f"subtitles='{srt_esc}':force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,MarginV=50,Bold=1'",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(final),
    ], capture_output=True, check=True)

    size_mb = final.stat().st_size / (1024 * 1024)
    print(f"  FINAL: {final}")
    print(f"  Size: {size_mb:.1f} MB")


# ============================================================
# MAIN
# ============================================================
def main():
    t0 = time.time()
    print("=" * 60)
    print("  PREMIUM VIDEO GENERATOR")
    print("  Handwriting + Characters + Whiteboard + Stats")
    print("=" * 60)

    asyncio.run(generate_all_audio())
    build_scene_videos()
    concatenate_all()
    merge_subtitles_and_finalize()

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  COMPLETE in {elapsed:.0f}s")
    print(f"  {OUT / 'Video_Workflow_Manager_PREMIUM.mp4'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
